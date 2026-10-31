pragma solidity 0.8.20;

contract Safe9639 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public deposits;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        total += msg.value;
    }
    bool private locked;

    function withdraw(uint256 amount) public {
        require(!locked);
        locked = true;
        require(deposits[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok);
        deposits[msg.sender] -= amount;
        total -= amount;
        locked = false;
    }

    function totalDeposits() public view returns (uint256) { return total; }

    function balanceOf(address who) public view returns (uint256) { return deposits[who]; }
}
