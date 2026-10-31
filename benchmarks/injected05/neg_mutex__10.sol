pragma solidity 0.5.12;

contract Vault8999 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public deposits;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        supply += msg.value;
    }
    bool private locked;

    function withdraw(uint256 amount) public {
        require(!locked);
        locked = true;
        require(deposits[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call.value(amount)("");
        require(ok);
        deposits[msg.sender] -= amount;
        supply -= amount;
        locked = false;
    }

    function balanceOf(address who) public view returns (uint256) { return deposits[who]; }

    function ownerOf_() public view returns (address) { return owner; }
}
