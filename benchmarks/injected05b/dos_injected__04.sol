pragma solidity 0.5.12;

contract Bank5459 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public balances;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        supply += msg.value;
    }
    address[] public members;

    function join() public {
        members.push(msg.sender);
    }

    function creditAll() public {
        for (uint256 i = 0; i < members.length; i++) {
            members[i].balance;
        }
    }

    function totalDeposits() public view returns (uint256) { return supply; }

    function balanceOf(address who) public view returns (uint256) { return balances[who]; }
}
