pragma solidity 0.8.20;

contract Ledger9185 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public deposits;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        supply += msg.value;
    }
    bool private locked;

    function withdraw(uint256 amount) public {
        require(!locked);
        locked = true;
        require(deposits[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok);
        deposits[msg.sender] -= amount;
        supply -= amount;
        locked = false;
    }

    function balanceOf(address who) public view returns (uint256) { return deposits[who]; }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
