pragma solidity 0.5.12;

contract Fund1147 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public balances;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        total += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        msg.sender.transfer(amount);
        balances[msg.sender] -= amount;
        total -= amount;
    }

    function balanceOf(address who) public view returns (uint256) { return balances[who]; }

    function totalDeposits() public view returns (uint256) { return total; }
}
